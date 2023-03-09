PROTOC_GEN_GRPC_PLUGIN="./node_modules/.bin/grpc_tools_node_protoc_plugin"
PROTOC_GEN_TS_PLUGIN="./node_modules/.bin/protoc-gen-ts"
PROTOS_SOURCE=$1

PROTO_DEST="./src/grpc"
mkdir -p $PROTO_DEST

yarn run grpc_tools_node_protoc \
    --js_out=import_style=commonjs,binary:${PROTO_DEST} \
    --grpc_out=${PROTO_DEST} \
    --plugin=protoc-gen-grpc=${PROTOC_GEN_GRPC_PLUGIN} \
    -I ${PROTOS_SOURCE} \
    ${PROTOS_SOURCE}/sub-unsub.proto \
    ${PROTOS_SOURCE}/ticket-bot.proto \
&& \
yarn run grpc_tools_node_protoc \
    --plugin=protoc-gen-ts=${PROTOC_GEN_TS_PLUGIN} \
    --ts_out=${PROTO_DEST} \
    -I ${PROTOS_SOURCE} \
    ${PROTOS_SOURCE}/sub-unsub.proto \
    ${PROTOS_SOURCE}/ticket-bot.proto
