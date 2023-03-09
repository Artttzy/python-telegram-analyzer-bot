/*
  Warnings:

  - Added the required column `callCenterKey` to the `SupportTicket` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "SupportTicket" ADD COLUMN     "callCenterKey" INTEGER NOT NULL;

-- CreateIndex
CREATE INDEX "SupportTicket_callCenterKey_idx" ON "SupportTicket"("callCenterKey");

-- AddForeignKey
ALTER TABLE "SupportTicket" ADD CONSTRAINT "SupportTicket_callCenterKey_fkey" FOREIGN KEY ("callCenterKey") REFERENCES "CallCenter"("id") ON DELETE CASCADE ON UPDATE CASCADE;
