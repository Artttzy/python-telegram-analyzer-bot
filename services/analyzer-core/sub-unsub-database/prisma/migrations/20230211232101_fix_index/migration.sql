/*
  Warnings:

  - A unique constraint covering the columns `[messageId,channelKey]` on the table `Message` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "Message_messageId_key";

-- CreateIndex
CREATE UNIQUE INDEX "Message_messageId_channelKey_key" ON "Message"("messageId", "channelKey");
