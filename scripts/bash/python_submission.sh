:

HOME_DIR=$PWD
PYTHON_FILE="energy_grep"
PYTHON_EXE_CMD="python3"

for WORK_DIR in ${HOME_DIR}/PPiMg2* ; do
    SYS_NAME=$(basename ${WORK_DIR})
    [ -d "${SYS_NAME}" ] || continue #checks whether it is a folder, if not it skips
    echo "Operating ${SYS_NAME} system."
    rm -f ${SYS_NAME}/*.png
    echo "${SYS_NAME}/*.png removed"
    PYTHON_FILE_PATH="${SYS_NAME}/${PYTHON_FILE}"
    sed -e "s/_R_SYS_NAME_/\"${SYS_NAME}\"/g" "${PYTHON_FILE_PATH}.py" > "${PYTHON_FILE_PATH}_${SYS_NAME}.py"
    echo "Moving inside ${SYS_NAME} folder"
    cd ${SYS_NAME}
    ${PYTHON_EXE_CMD} "${PYTHON_FILE}_${SYS_NAME}.py" || { echo "Was not possible to run the python script. Aborting..."; exit 1 ;}
    echo "PNG file have been succesfully generated"
    echo "Going back to ${HOME_DIR}"
    cd ${HOME_DIR}
done

sleep 2
echo "Have a good day!"
