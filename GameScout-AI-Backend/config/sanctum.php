<?php
return [
    'stateful' => explode(',', env('SANCTUM_STATEFUL_DOMAINS', '127.0.0.1:5173,localhost:5173')),
    'guard' => ['web'],
    'expiration' => null,
];
