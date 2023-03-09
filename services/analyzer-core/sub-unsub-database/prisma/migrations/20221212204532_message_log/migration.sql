-- AlterTable
ALTER TABLE "SupportTicket" ADD COLUMN     "agentMessages" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "userMessages" INTEGER NOT NULL DEFAULT 0;

-- CreateTable
CREATE TABLE "TicketMessage" (
    "id" SERIAL NOT NULL,
    "messageId" VARCHAR(32) NOT NULL,
    "ticketKey" INTEGER NOT NULL,

    CONSTRAINT "TicketMessage_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "TicketMessage_ticketKey_idx" ON "TicketMessage"("ticketKey");

-- CreateIndex
CREATE UNIQUE INDEX "TicketMessage_messageId_key" ON "TicketMessage"("messageId");

-- AddForeignKey
ALTER TABLE "TicketMessage" ADD CONSTRAINT "TicketMessage_ticketKey_fkey" FOREIGN KEY ("ticketKey") REFERENCES "SupportTicket"("id") ON DELETE CASCADE ON UPDATE CASCADE;
