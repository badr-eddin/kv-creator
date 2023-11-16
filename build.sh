python3 ./src/tmp/rcc.py "$(pwd)"
mv ./src/tmp/app-qrc.qrc ./app-qrc.qrc
pyrcc5 ./app-qrc.qrc -o ./libs/db/resources.py
mv ./app-qrc.qrc ./src/tmp/app-qrc.qrc
sed -i -r 's/PyQt5/PyQt6/g' ./libs/db/resources.py
sed -i '1,8d' ./libs/db/resources.py