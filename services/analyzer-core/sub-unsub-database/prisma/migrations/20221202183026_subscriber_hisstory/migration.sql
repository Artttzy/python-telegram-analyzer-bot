-- CreateTable
CREATE TABLE "SubscriberHistory" (
    "id" SERIAL NOT NULL,
    "channelId" VARCHAR(32) NOT NULL,
    "measureTime" TIMESTAMPTZ(3) NOT NULL,
    "subscriberCount" INTEGER NOT NULL,

    CONSTRAINT "SubscriberHistory_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "SubscriberHistory_channelId_idx" ON "SubscriberHistory"("channelId");
