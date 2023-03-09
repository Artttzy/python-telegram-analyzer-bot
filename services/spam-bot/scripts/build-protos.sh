PROTOS_PATH=$1
GRPC_OUT="./"
mkdir -p $GRPC_OUT

python -m grpc_tools.protoc -I $PROTOS_PATH --python_out=$GRPC_OUT --pyi_out=$GRPC_OUT --grpc_python_out=$GRPC_OUT \
${PROTOS_PATH}/sub-unsub.proto ${PROTOS_PATH}/ticket-bot.proto