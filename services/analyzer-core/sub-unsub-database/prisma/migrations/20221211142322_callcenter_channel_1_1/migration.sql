/*
  Warnings:

  - A unique constraint covering the columns `[channelKey]` on the table `CallCenter` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "CallCenter_channelKey_idx";

-- CreateIndex
CREATE UNIQUE INDEX "CallCenter_channelKey_key" ON "CallCenter"("channelKey");
