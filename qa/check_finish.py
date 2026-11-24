"""Find each run's last saved solution and distinguish actual solver convergence."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('case_dir',nargs='+',type=Path)
args=p.parse_args()
for path in args.case_dir:
    metric=path/'metrics.json'
    if not metric.is_file():
        print(json.dumps({'path':str(path),'status':'pending'})); continue
    m=json.loads(metric.read_text())
    log=(path/'run.log').read_text(errors='replace')
    phase=[line for line in log.splitlines() if 'Successfully applied boundary conditions; solving in reduced space' in line]
    end=m.get('final_solver_summary','')
    m['final_fit_converged']=bool(phase) and 'Gradient vector norm too small' in end and m.get('solver_reported_success',False) and m.get('returncode')==0
    m['garment_export_exists']=(path/'garment_final.obj').is_file()
    m['failures_recorded']=sum(l for l in [log.count('[error]'),log.count('Reached iteration limit')])
    print(json.dumps(m,ensure_ascii=False,indent=2))
