
import wandb
import numpy as np
from sklearn import datasets
from sklearn.model_selection import KFold
import multiprocessing
from sklearn.linear_model import Lasso
import os
import argparse
import collections


Worker = collections.namedtuple("Worker", ("queue", "process"))
WorkerInitData = collections.namedtuple(
    "WorkerInitData", ("num", "sweep_id", "sweep_run_name", "config")
)
WorkerDoneData = collections.namedtuple("WorkerDoneData", ("score"))

def reset_wandb_env():
    exclude = {
        "WANDB_PROJECT",
        "WANDB_ENTITY",
        "WANDB_API_KEY",
    }
    for k, v in os.environ.items():
        if k.startswith("WANDB_") and k not in exclude:
            del os.environ[k]


def train(sweep_q, worker_q, fold, train_index, test_index):
    reset_wandb_env()
    worker_data = worker_q.get()
    config = worker_data.config
    run_name = "{}-{}".format(worker_data.sweep_run_name, worker_data.num)

    ## start the run within the process
    run = wandb.init(group = worker_data.sweep_id,
                     job_type = worker_data.sweep_run_name, 
                     name = run_name, 
                     config = config
                     )
    ## load data
    X, y = datasets.load_diabetes(return_X_y=True)
    ## create model
    lasso = Lasso(alpha = wandb.config.alpha, random_state=0, max_iter=10000)
    ## fit model
    lasso.fit(X[train_index], y[train_index])
    ## score test data
    score = lasso.score(X[test_index], y[test_index])
    ## log score to wandb 
    run.log({"score": score, "fold": fold})
    ## finish current run
    wandb.finish()
    ## write the metric back to the sweep queue.  
    sweep_q.put(WorkerDoneData(score= score))

def main(args):

    sweep_q = multiprocessing.Queue() 
    num_folds = 5
    kf = KFold(n_splits=num_folds)
    X, y = datasets.load_diabetes(return_X_y=True)
    sweep_q = multiprocessing.Queue()
    workers = []

    for num, (train_index, test_index) in enumerate(kf.split(X)):
        q = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=train, kwargs=dict(sweep_q=sweep_q, worker_q=q, fold = num, train_index = train_index, test_index = test_index)
        )
        p.start()
        workers.append(Worker(queue=q, process=p))
    
    ## main run for a given sweep.  
    ## the details of this run will be passed around to the 
    ## runs that get created when the train function is called
    ## this provides you with the ability to group runs based on sweep 
    ## details in the main W&B UI.  
    sweep_run = wandb.init()
    sweep_id = sweep_run.sweep_id or "unknown"
    sweep_url = sweep_run.get_sweep_url()
    project_url = sweep_run.get_project_url()

    sweep_run.notes = "something goes here"
    sweep_run.save()
    sweep_run_name = sweep_run.name or sweep_run.id or "unknown"

    metrics = []
    for num in range(num_folds):
        worker = workers[num]
        # start worker and pass details of main sweep run. 
        worker.queue.put(
            WorkerInitData(
                sweep_id=sweep_id,
                num=num,
                sweep_run_name=sweep_run_name,
                config= {"alpha": args.alpha},
            )
        )
        # get metric from worker
        result = sweep_q.get()
        # wait for worker to finish
        worker.process.join()
        # log metric to sweep_run
        metrics.append(result.score)
    for m in metrics:
        print(m)
    ## log the metrics to the main sweep run
    sweep_run.log({"score": sum(metrics)/len(metrics), "folds": 5 })
    ## finish the main sweep run
    wandb.finish()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--alpha', type=float)
    args = parser.parse_args()
    # run = wandb.init(config=args)
    main(args)