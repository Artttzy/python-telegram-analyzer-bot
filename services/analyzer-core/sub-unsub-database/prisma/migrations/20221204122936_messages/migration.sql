-- CreateTable
CREATE TABLE "Message" (
    "id" SERIAL NOT NULL,
    "channelKey" INTEGER NOT NULL,
    "messageId" TEXT NOT NULL,
    "measureTime" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "Message_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "Message_channelKey_idx" ON "Message"("channelKey");

-- CreateIndex
CREATE UNIQUE INDEX "Message_messageId_key" ON "Message"("messageId");

-- AddForeignKey
ALTER TABLE "Message" ADD CONSTRAINT "Message_channelKey_fkey" FOREIGN KEY ("channelKey") REFERENCES "AdminChannel"("id") ON DELETE CASCADE ON UPDATE CASCADE;
