import wandb
wandb.init(config = dict(a = 0.5))
a = wandb.config.a
for i in range(10):
  wandb.log(dict( S = (1 - a**i)/(1 - a)))
wandb.finish()