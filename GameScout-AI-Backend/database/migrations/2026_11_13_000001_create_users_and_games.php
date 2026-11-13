<?php
declare(strict_types=1);
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void {
        Schema::create('users',function (Blueprint $table): void {
            $table->id(); $table->string('name'); $table->string('email')->unique();
            $table->string('password'); $table->rememberToken(); $table->timestamps();
        });
        Schema::create('games',function (Blueprint $table): void {
            $table->id(); $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('game_id',128); $table->string('platform',10); $table->string('external_app_id');
            $table->string('title'); $table->string('developer_profile',20); $table->string('source_record_id');
            $table->jsonb('normalized_genres'); $table->string('data_origin',30); $table->timestamps();
            $table->unique(['user_id','platform','external_app_id']);
        });
    }
    public function down(): void { Schema::dropIfExists('games'); Schema::dropIfExists('users'); }
};
