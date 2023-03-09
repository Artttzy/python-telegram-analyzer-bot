/*
  Warnings:

  - You are about to drop the column `userId` on the `CallCenter` table. All the data in the column will be lost.

*/
-- DropIndex
DROP INDEX "CallCenter_userId_key";

-- AlterTable
ALTER TABLE "CallCenter" DROP COLUMN "userId";

-- CreateIndex
CREATE INDEX "CallCenter_channelKey_idx" ON "CallCenter"("channelKey");
