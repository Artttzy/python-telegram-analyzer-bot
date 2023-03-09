import bot_manager_pb2_grpc
import bot_manager_pb2
import docker
import util

client = docker.from_env()


class BotManagerServicer(bot_manager_pb2_grpc.BotManagerServicer):
    def CreateBot(self, request, context):
        bot_token: str = request.bot_token
        channel_id = request.bot_channel_id
        call_center = request.bot_callcenter

        image = client.images.get('tech-support-template:latest')
        container_name = util.get_container_name(token=bot_token)
        client.containers.run(
            image=image,
            detach=True,
            name=container_name,
            environment=[
                f'CHANNEL_ID={channel_id}',
                f'CALL_CENTER_ID={call_center}',
                f'BOT_TOKEN={bot_token}',
            ],
            restart_policy={'Name': 'always'}
        )

        return bot_manager_pb2.BotResponse()

    def DeleteBot(self, request, context):
        bot_token = request.bot_token
        container_name = util.get_container_name(token=bot_token)
        container = client.containers.get(container_id=container_name)

        try:
            container.kill()
        except Exception as e:
            pass

        try:
            container.remove()
        except Exception as e:
            pass

        return bot_manager_pb2.BotResponse()

    def CreateSpamBot(self, request, context):
        bot_token: str = request.bot_token
        channel_id = request.bot_channel_id

        image = client.images.get('announe-template:latest')
        container_name = util.get_container_name(token=bot_token)
        client.containers.run(
            image=image,
            detach=True,
            name=container_name,
            environment=[
                f'CHANNEL_ID={channel_id}',
                f'BOT_TOKEN={bot_token}',
            ],
            restart_policy={'Name': 'always'}
        )

        return bot_manager_pb2.BotResponse()
