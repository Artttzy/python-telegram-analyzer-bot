import grpc
import sub_unsub_pb2_grpc
import sub_unsub_pb2

def getAdminById(userId: str):
    with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
        request = sub_unsub_pb2.UserIdRequest(userId=userId)
        response: sub_unsub_pb2.NullableAdmin = stub.GetAdminByUserId(request=request)
        
        if response.WhichOneof('adminOrNull') == 'empty':
            return None
        else:
            return response.admin
