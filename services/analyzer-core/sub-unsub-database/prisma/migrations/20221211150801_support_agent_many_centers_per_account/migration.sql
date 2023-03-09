/*
  Warnings:

  - A unique constraint covering the columns `[userId,callCenterKey]` on the table `SupportAgent` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "SupportAgent_userId_key";

-- CreateIndex
CREATE UNIQUE INDEX "SupportAgent_userId_callCenterKey_key" ON "SupportAgent"("userId", "callCenterKey");
