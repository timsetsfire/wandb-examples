import wandb
wandb.init(config = dict(a = 0.5, N = 10))
a = wandb.config.a
for i in range(10):
  S_N = (1 - a**i) / (1 - a)
  wandb.log(dict( S_N = S_N) )
  if np.abs(a) < 1:
    err = 1 / (1 - a) - S_N
  else:
    err = np.infty
  wandb.log({"error": err})
wandb.finish()
