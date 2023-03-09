-- CreateTable
CREATE TABLE "AnnounceBotMessage" (
    "id" SERIAL NOT NULL,
    "announceBotKey" INTEGER NOT NULL,
    "channelId" VARCHAR(32) NOT NULL,
    "messageId" VARCHAR(32) NOT NULL,
    "messageType" VARCHAR(5) NOT NULL,

    CONSTRAINT "AnnounceBotMessage_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "AnnounceBotMessage_announceBotKey_idx" ON "AnnounceBotMessage"("announceBotKey");

-- CreateIndex
CREATE INDEX "AnnounceBotMessage_messageType_idx" ON "AnnounceBotMessage"("messageType");

-- CreateIndex
CREATE UNIQUE INDEX "AnnounceBotMessage_channelId_messageId_key" ON "AnnounceBotMessage"("channelId", "messageId");

-- AddForeignKey
ALTER TABLE "AnnounceBotMessage" ADD CONSTRAINT "AnnounceBotMessage_announceBotKey_fkey" FOREIGN KEY ("announceBotKey") REFERENCES "AnnounceBot"("id") ON DELETE CASCADE ON UPDATE CASCADE;
