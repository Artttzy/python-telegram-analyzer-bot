-- CreateTable
CREATE TABLE "SupportRedirect" (
    "id" SERIAL NOT NULL,
    "channelKey" INTEGER NOT NULL,
    "clickTime" TIMESTAMPTZ(3) NOT NULL,
    "count" INTEGER NOT NULL,

    CONSTRAINT "SupportRedirect_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "SupportRedirect_channelKey_idx" ON "SupportRedirect"("channelKey");

-- AddForeignKey
ALTER TABLE "SupportRedirect" ADD CONSTRAINT "SupportRedirect_channelKey_fkey" FOREIGN KEY ("channelKey") REFERENCES "AdminChannel"("id") ON DELETE CASCADE ON UPDATE CASCADE;
