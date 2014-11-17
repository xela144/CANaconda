#include "canaconda_mainwindow.h"
#include "ui_canaconda_mainwindow.h"

CANaconda_MainWindow::CANaconda_MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::CANaconda_MainWindow)
{
    ui->setupUi(this);
}

CANaconda_MainWindow::~CANaconda_MainWindow()
{
    delete ui;
}
