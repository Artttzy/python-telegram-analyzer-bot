/*
  Warnings:

  - You are about to drop the column `channelId` on the `SubscriberHistory` table. All the data in the column will be lost.
  - Added the required column `channelKey` to the `SubscriberHistory` table without a default value. This is not possible if the table is not empty.

*/
-- DropIndex
DROP INDEX "SubscriberHistory_channelId_idx";

-- AlterTable
ALTER TABLE "SubscriberHistory" DROP COLUMN "channelId",
ADD COLUMN     "channelKey" INTEGER NOT NULL;

-- CreateIndex
CREATE INDEX "SubscriberHistory_channelKey_idx" ON "SubscriberHistory"("channelKey");

-- AddForeignKey
ALTER TABLE "SubscriberHistory" ADD CONSTRAINT "SubscriberHistory_channelKey_fkey" FOREIGN KEY ("channelKey") REFERENCES "AdminChannel"("id") ON DELETE CASCADE ON UPDATE CASCADE;
