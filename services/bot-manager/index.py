import grpc
from concurrent import futures
import bot_manager_pb2_grpc
import bot_manager_server


def main():
    server = grpc.server(futures.ThreadPoolExecutor())
    bot_manager_pb2_grpc.add_BotManagerServicer_to_server(
        servicer=bot_manager_server.BotManagerServicer(),
        server=server
    )

    server.add_insecure_port('0.0.0.0:40001')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    main()
