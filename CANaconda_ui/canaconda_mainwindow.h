#ifndef CANACONDA_MAINWINDOW_H
#define CANACONDA_MAINWINDOW_H

#include <QMainWindow>

namespace Ui {
class CANaconda_MainWindow;
}

class CANaconda_MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit CANaconda_MainWindow(QWidget *parent = 0);
    ~CANaconda_MainWindow();

private:
    Ui::CANaconda_MainWindow *ui;
};

#endif // CANACONDA_MAINWINDOW_H
