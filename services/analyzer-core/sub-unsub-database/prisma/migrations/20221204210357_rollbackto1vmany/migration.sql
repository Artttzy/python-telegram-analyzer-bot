-- DropIndex
DROP INDEX "SupportRedirect_channelKey_key";

-- CreateIndex
CREATE INDEX "SupportRedirect_channelKey_idx" ON "SupportRedirect"("channelKey");
