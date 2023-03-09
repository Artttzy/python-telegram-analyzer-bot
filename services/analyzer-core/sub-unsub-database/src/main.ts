import { Server, ServerCredentials } from 'grpc'
import { SubscribtionServiceService } from './grpc/sub-unsub_grpc_pb';
import { TicketsService } from './grpc/ticket-bot_grpc_pb';
import { SubUnsubServer } from './services/SubUnsubServer';
import { TicketBotServerV2 } from './services/TicketBotServerV2';

const server = new Server();
server.addService(SubscribtionServiceService as any, new SubUnsubServer() as any);
server.addService(TicketsService as any, new TicketBotServerV2() as any);
server.bind(`0.0.0.0:50001`, ServerCredentials.createInsecure());
server.start();
console.log('Server started')