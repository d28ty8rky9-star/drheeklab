"""Least-privilege Windows Task Scheduler; no password in arguments or task XML."""
from pathlib import Path
import csv
import hashlib
import os
import subprocess
import sys
import tempfile
from datetime import date
import xml.etree.ElementTree as ET

NS='http://schemas.microsoft.com/windows/2004/02/mit/task'
IS_WINDOWS=os.name=='nt'
ET.register_namespace('',NS)

def task_name(root,environment):
    return 'DrHeekLab-Backup-'+environment+'-'+hashlib.sha256(str(Path(root).resolve()).casefold().encode()).hexdigest()[:12]

def task_xml(root,environment,hour='18:00',destination=None,*,sid,executable=None,frozen=None):
    from .storage import ENVIRONMENTS
    if environment not in ENVIRONMENTS:raise ValueError('Ambiente inválido')
    from datetime import datetime
    try:datetime.strptime(hour,'%H:%M')
    except ValueError:raise ValueError('Horário deve ser HH:MM.') from None
    executable=str(executable or sys.executable)
    frozen=getattr(sys,'frozen',False) if frozen is None else frozen
    arguments=[] if frozen else ['-m','drheeklab']
    arguments+=['--scheduled-backup','--environment',environment,'--data-dir',str(Path(root).resolve())]
    if destination:arguments+=['--backup-destination',str(Path(destination).resolve())]
    task=ET.Element('{'+NS+'}Task',version='1.2')
    def node(parent,name,text=None):
        item=ET.SubElement(parent,'{'+NS+'}'+name)
        if text is not None:item.text=text
        return item
    registration=node(task,'RegistrationInfo');node(registration,'Description','Backup diário verificado Dr. Heek Lab; usuário conectado, aplicativo aberto ou fechado. Sem criptografia; proteja a pasta. Não cria ambientes novos.')
    triggers=node(task,'Triggers');daily=node(triggers,'CalendarTrigger')
    repeat=node(daily,'Repetition');node(repeat,'Interval','PT1H');node(repeat,'Duration','P1D');node(repeat,'StopAtDurationEnd','false')
    node(daily,'StartBoundary',date.today().isoformat()+'T'+hour+':00');node(daily,'Enabled','true');schedule=node(daily,'ScheduleByDay');node(schedule,'DaysInterval','1')
    login=node(triggers,'LogonTrigger');node(login,'Enabled','true');node(login,'UserId',sid)
    principals=node(task,'Principals');principal=node(principals,'Principal');principal.set('id','Owner');node(principal,'UserId',sid);node(principal,'LogonType','InteractiveToken');node(principal,'RunLevel','LeastPrivilege')
    settings=node(task,'Settings');node(settings,'MultipleInstancesPolicy','IgnoreNew');node(settings,'DisallowStartIfOnBatteries','false');node(settings,'StopIfGoingOnBatteries','false');node(settings,'StartWhenAvailable','true');node(settings,'Enabled','true');node(settings,'ExecutionTimeLimit','PT2H')
    actions=node(task,'Actions');actions.set('Context','Owner');run=node(actions,'Exec');node(run,'Command',executable);node(run,'Arguments',subprocess.list2cmdline(arguments));node(run,'WorkingDirectory',str(Path(executable).parent))
    return ET.tostring(task,encoding='unicode',xml_declaration=False)

def current_sid():
    result=subprocess.run(['whoami','/user','/fo','csv','/nh'],capture_output=True,text=True,check=True)
    sid=next(csv.reader(result.stdout.splitlines()))[-1]
    if not sid.startswith('S-1-'):raise ValueError('Não foi possível identificar usuário Windows.')
    return sid

def install_task(storage,hour='18:00',destination=None):
    if not IS_WINDOWS:raise ValueError('Agendamento automático requer Windows. Backup manual permanece disponível.')
    xml=task_xml(storage.root,storage.environment,hour,destination,sid=current_sid())
    with tempfile.TemporaryDirectory(prefix='drheek-task-') as temp:
        file=Path(temp)/'task.xml';file.write_text(xml,encoding='utf-16')
        result=subprocess.run(['schtasks','/Create','/TN',task_name(storage.root,storage.environment),'/XML',str(file),'/F'],capture_output=True,text=True)
        if result.returncode:raise ValueError('Windows não permitiu criar a tarefa. Use configuração assistida; nenhum dado foi alterado.')
    storage.set('backup_task',{'name':task_name(storage.root,storage.environment),'hour':hour,'destination':str(destination) if destination else None,'encrypted':False})
    return storage.get('backup_task')

def remove_task(storage):
    if not IS_WINDOWS:raise ValueError('Agendamento automático requer Windows.')
    name=task_name(storage.root,storage.environment)
    result=subprocess.run(['schtasks','/Delete','/TN',name,'/F'],capture_output=True,text=True)
    if result.returncode:raise ValueError('Não foi possível remover a tarefa; confira o Agendador de Tarefas.')
    storage.set('backup_task',None)

def export_task(storage,path,hour='18:00',destination=None):
    if not IS_WINDOWS:raise ValueError('Exportação da tarefa requer Windows para identificar o usuário atual.')
    Path(path).write_text(task_xml(storage.root,storage.environment,hour,destination,sid=current_sid()),encoding='utf-16')
