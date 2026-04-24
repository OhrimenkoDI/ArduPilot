создал среду
python -m venv myenv

Выбор среды 
 .\venv\Scripts\activate

установол прокси ardupilot
pip install mavproxy
python -m pip install prompt_toolkit
python -m pip install wxPython
pip install pymavlink


///////////////////////////////////////
На Orange:

pip install pymavlink


Включение UART3 (Orange Pi OS / Armbian)

sudo nano /boot/orangepiEnv.txt
Добавь строку:
overlays=uart3-m1
Если уже есть overlays= — добавь через пробел:
overlays=uart3-m1 spi0-m1
