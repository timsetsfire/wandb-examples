import wandb
import numpy as np
wandb.init(config = dict(r = 1, a = 0.5, N = 10))
a = wandb.config.a
r = wandb.config.r
for i in range(wandb.config.N):
  S_N = (1 - a**i) / (1 - a)
  S_N *= r
  wandb.log(dict( S_N = S_N) )
  if np.abs(a) < 1:
    err = r / (1 - a) - S_N
  else:
    err = np.infty
  wandb.log({"error": err})
wandb.finish()
