# Policy Gradient Agent 
#   - REINFORCE with policy approximation
#
# ---
# @author Yiren Lu
# @email luyiren [at] seas [dot] upenn [dot] edu
#
# MIT License
import gym
import numpy as np
import random
import tensorflow as tf
import tensorflow.contrib.slim as slim
import tf_utils


class PolicyGradientNNAgent():

  def __init__(self,
    lr=0.5, 
    gamma=0.99, 
    state_size=4,
    action_size=2,
    n_hidden_1=20,
    n_hidden_2=20,
    scope="pg"
    ):
    """
    args
      epsilon           exploration rate
      epsilon_anneal    linear decay rate per call of learn() function (iteration)
      end_epsilon       lowest exploration rate
      lr                learning rate
      gamma             discount factor
      state_size        network input size
      action_size       network output size
    """
    self.lr = lr
    self.gamma = gamma
    self.state_size = state_size
    self.action_size = action_size
    self.total_steps = 0
    self.n_hidden_1 = n_hidden_1
    self.n_hidden_2 = n_hidden_2
    self.scope = scope

    self._build_policy_net()



  def _build_policy_net(self):
    """Build policy network"""
    with tf.variable_scope(self.scope):
      # input state
      self.state_input = tf.placeholder(tf.float32, [None, self.state_size])
      # input action to generate output mask
      self.action = tf.placeholder(tf.int32, [None])

      self.target = tf.placeholder(tf.float32, [None])

      layer_1 = tf_utils.fc(self.state_input, self.n_hidden_1, tf.nn.relu)
      layer_2 = tf_utils.fc(layer_1, self.n_hidden_2, tf.nn.relu)

      self.value = tf_utils.fc(layer_2, 1)

      self.action_values = tf_utils.fc(layer_2, self.action_size)

      action_mask = tf.one_hot(self.action, self.action_size, 1.0, 0.0)
      self.action_value_pred = tf.reduce_sum(self.action_values * action_mask, 1)
      
      self.pg_loss = tf.reduce_mean(-tf.log(self.action_value_pred) * self.target)
      self.loss = self.pg_loss

      self.optimizer = tf.train.AdamOptimizer(learning_rate=self.lr)
      self.train_op = self.optimizer.minimize(
      self.loss, global_step=tf.contrib.framework.get_global_step())


  def get_action(self, state, sess):
    """
    Epsilon-greedy action
    args
      state           current state      
    returns
      an action to take given the state
    """
    # pi = self.get_policy(state, sess)
    # return np.random.choice(range(self.action_size), p=pi)
    pi = sess.run(self.action_values, feed_dict={self.state_input: [state]})    
    return pi.argmax()


  def get_policy(self, state, sess):
    """returns policy as probability distribution of actions"""
    pi = sess.run(self.action_values, feed_dict={self.state_input: [state]})    
    pi = [np.exp(p) for p in pi[0]]
    z = sum(pi)
    pi = [p/z for p in pi]
    return pi


  def learn(self, episode, sess, train_epoch = 1):
    for t in xrange(len(episode)):
      self.total_steps = self.total_steps + 1
      target = sum([self.gamma**i * r for i, (s, a, s1, r, d) in enumerate(episode[t:])])
      state, action, next_state, reward, done = episode[t]
      feed_dict = { self.state_input: [state], self.target: [target], self.action: [action] }
      _, loss = sess.run([self.train_op, self.loss], feed_dict)