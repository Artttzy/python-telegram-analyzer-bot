-- CreateTable
CREATE TABLE "AnnounceBot" (
    "id" SERIAL NOT NULL,
    "channelKey" INTEGER NOT NULL,

    CONSTRAINT "AnnounceBot_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "AnnounceBot_channelKey_key" ON "AnnounceBot"("channelKey");

-- AddForeignKey
ALTER TABLE "AnnounceBot" ADD CONSTRAINT "AnnounceBot_channelKey_fkey" FOREIGN KEY ("channelKey") REFERENCES "AdminChannel"("id") ON DELETE CASCADE ON UPDATE CASCADE;
