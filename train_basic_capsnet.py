import numpy as np
from tensorflow.keras import optimizers
from tensorflow.keras import callbacks
from bmstu.capsnets import models, losses
from bmstu import utls
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--epochs', default=5)
parser.add_argument('--batch_size', default=100)
parser.add_argument('--routings', default=3)
parser.add_argument('--save_dir', default='./')
parser.add_argument('--dataset', default='mnist', help='value: mnist, fashion_mnist, cifar10, cifar100')
parser.add_argument('--lr', default=0.001)
parser.add_argument('--lr_decay', default=0.9)
parser.add_argument('--lam_recon', default=0.392)


if __name__ == '__main__':
    # CapsNet Mnist
    args = parser.parse_args()

    # load data
    (x_train, y_train), (x_test, y_test) = utls.load(args.dataset)
    # define model

    model, eval_model, manipulate_model = models.CapsNet(shape=x_train.shape[1:],
                                                         num_classes=len(np.unique(np.argmax(y_train, 1))),
                                                         routings=args.routings).build()

    model.summary()

    # callbacks
    log = callbacks.CSVLogger(args.save_dir + '/log.csv')
    tb = callbacks.TensorBoard(log_dir=args.save_dir + '/tensorboard-logs',
                               batch_size=args.batch_size, histogram_freq=int(args.debug))
    checkpoint = callbacks.ModelCheckpoint(args.save_dir + '/weights-{epoch:02d}.h5', monitor='val_capsnet_acc',
                                           save_best_only=True, save_weights_only=True, verbose=1)
    lr_decay = callbacks.LearningRateScheduler(schedule=lambda epoch: args.lr * (args.lr_decay ** epoch))

    # compile the model
    model.compile(optimizer=optimizers.Adam(lr=args.lr),
                  loss=[losses.margin_loss, 'mse'],
                  loss_weights=[1., args.lam_recon],
                  metrics={'capsnets': 'accuracy'})

    model.fit([x_train, y_train], [y_train, x_train], batch_size=args.batch_size, epochs=args.epochs,
              validation_data=[[x_test, y_test], [y_test, x_test]], callbacks=[log, tb, checkpoint, lr_decay])

    model.save_weights(f'{args.save_dir}/trained_basic_capsnet_model_{args.dataset}.h5')
    eval_model.save_weights(f'{args.save_dir}/eval_basic_capsnet_model_{args.dataset}.h5')
    manipulate_model.save_weights(f'{args.save_dir}/manipulate_basic_capsnet_model_{args.dataset}.h5')

    print(f'Trained model saved to \'{args.save_dir}/trained_basic_capsnet_model_{args.dataset}.h5\'')
    print(f'Evaluated model saved to \'{args.save_dir}/eval_basic_capsnet_model_{args.dataset}.h5\'')
    print(f'Manipulated model saved to \'{args.save_dir}/manipulate_basic_capsnet_model_{args.dataset}.h5\'')

    utls.plot_log(args.save_dir + '/log.csv', show=True)
