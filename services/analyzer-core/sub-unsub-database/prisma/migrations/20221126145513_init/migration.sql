-- CreateTable
CREATE TABLE "Event" (
    "id" SERIAL NOT NULL,
    "userId" INTEGER NOT NULL,
    "channelId" INTEGER NOT NULL,
    "eventTime" TIMESTAMP(3) NOT NULL,
    "eventStatus" VARCHAR(20) NOT NULL,

    CONSTRAINT "Event_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "Event_userId_idx" ON "Event"("userId");

-- CreateIndex
CREATE INDEX "Event_channelId_idx" ON "Event"("channelId");

-- CreateIndex
CREATE INDEX "Event_eventStatus_idx" ON "Event"("eventStatus");
