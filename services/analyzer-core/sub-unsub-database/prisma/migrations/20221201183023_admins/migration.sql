-- CreateTable
CREATE TABLE "Admin" (
    "id" SERIAL NOT NULL,
    "userId" VARCHAR(32) NOT NULL,
    "superuser" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "Admin_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Admin_userId_key" ON "Admin"("userId");
