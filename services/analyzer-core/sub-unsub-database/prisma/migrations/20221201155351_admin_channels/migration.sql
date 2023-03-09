-- CreateTable
CREATE TABLE "AdminChannel" (
    "id" SERIAL NOT NULL,
    "channelId" VARCHAR(32) NOT NULL,
    "channelName" TEXT NOT NULL,

    CONSTRAINT "AdminChannel_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "AdminChannel_channelId_key" ON "AdminChannel"("channelId");
