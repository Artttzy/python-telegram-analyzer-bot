/*
  Warnings:

  - A unique constraint covering the columns `[activeTicketKey]` on the table `SupportAgent` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "SupportAgent" ADD COLUMN     "activeTicketKey" INTEGER;

-- CreateIndex
CREATE INDEX "SupportAgent_callCenterKey_idx" ON "SupportAgent"("callCenterKey");

-- CreateIndex
CREATE UNIQUE INDEX "SupportAgent_activeTicketKey_key" ON "SupportAgent"("activeTicketKey");

-- AddForeignKey
ALTER TABLE "SupportAgent" ADD CONSTRAINT "SupportAgent_activeTicketKey_fkey" FOREIGN KEY ("activeTicketKey") REFERENCES "SupportTicket"("id") ON DELETE SET NULL ON UPDATE CASCADE;
