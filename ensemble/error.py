import numpy as np
import pickle
import math
import scipy.sparse as sparse
import scipy.stats as stats
import matplotlib.pyplot as plt
import scipy.optimize as optimize
import random

# Parameter size
directory_path = './../'
data_path = directory_path + 'data/'
subset_size = 50000
k = 10

# Paths
output_path = data_path + 'ensemble_dump_08.p'
test_users_path = data_path + 'test_users_04.p'
games_map_path = data_path + 'train_games_08.p'
user_map_path = data_path + 'train_user_map_08.p'
train_mat_path = data_path + 'train_user_mat_08.npz'
bias_path = data_path + 'train_bias_08.p'


# Imports
output = {}
with open(output_path, 'rb') as f:
    output = pickle.load(f)
    f.close()

bias = []
with open(bias_path, 'rb') as f:
    bias = pickle.load(f)
    f.close()
init_mu = bias[0]
init_buvec = bias[1]
init_bivec = bias[2]
del bias

buvec = output['bu']
bivec = output['bi']
pearson = output['pearson']
mu = output['mu']
p = output['p']
q = output['q']
wij = output['wij']

del output

user_map = {}
with open(user_map_path, 'rb') as f:
    user_map = pickle.load(f)
    f.close()

games_map = {}
with open(games_map_path, 'rb') as f:
    games_map = pickle.load(f)
    f.close()

test_users = {}
with open(test_users_path, 'rb') as f:
    test_users = pickle.load(f)
    f.close()

train_mat = sparse.load_npz(train_mat_path)
print(len(user_map))
num_users = train_mat.shape[0]
for user, ind in user_map.items():
    if ind >= num_users:
        print('How')

# Grab examples
test_instances = []
for user, game_dict in test_users.items():
    for game, hours in game_dict.items():
        hours = float(hours)
        if hours > 6:
            hours = 6
        elif hours < 1:
            hours = 1
        test_instances.append((user, game, hours))

test_subset = random.sample(test_instances, 50000)

# Calculate objective function value
pred = np.zeros(len(test_instances))
true = np.zeros(len(test_instances))
count = 0
for user, game, rui in test_instances:
    rhat = 0
    user_ind = None
    if user in user_map:
        user_ind = user_map[user]
    game_ind = None
    if game in games_map:
        game_ind = games_map[game]

    if game_ind is not None and user_ind is not None:
        rel_pearson = pearson[game_ind, :]
        order = np.argsort(rel_pearson)
        orderdescending = order[::-1]
        uservect = train_mat[user_ind, :]
        bu = buvec[0, user_ind]
        bi = bivec[0, game_ind]
        bui = mu + bu + bi
        uhb = uservect[0, orderdescending[1:k+1]] != 0
        Rk = np.sum(uhb)
        Rk = Rk + 1 * (Rk == 0)
        Rk_term = (1/(np.sqrt(Rk)))
        inner_term = uservect[0, orderdescending[1:k+1]] - \
            (init_mu+init_buvec[0, user_ind] +
             init_bivec[0, orderdescending[1:k+1]])
        # print(inner_term)
        inner_sum = uhb.multiply(inner_term)
        # print(inner_sum.shape)
        summation = np.dot(inner_sum.toarray(),
                           wij[orderdescending[1:k+1], game_ind])
        # print(summation.shape)
        rhat = bui + np.dot(q[game_ind, :], p[user_ind, :]
                            ) + Rk_term * summation
    elif game_ind is None and user_ind is not None:
        bu = buvec[0, user_ind]
        bui = mu + bu
        rhat = bui
    elif game_ind is not None and user_ind is None:
        bi = bivec[0, game_ind]
        bui = mu + bi
        rhat = bui
    else:
        rhat = mu
    pred[count] = rhat
    true[count] = rui
    count += 1
    if count % 1000 == 0:
        print(count)

# Calculate RMSE
print("RMSE: " + np.sqrt(np.mean(pred - true)**2))
