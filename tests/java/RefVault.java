// SPDX-License-Identifier: AGPL-3.0-only
// The reference: Cryptomator's own libraries (cryptofs and cryptolib, from Cryptomator.app) make test vaults and
// read vaults back, so Encryptor-MCP's results can be checked against the official code in both directions.
//
//   java -cp "<Cryptomator.app>/Contents/app/mods/*" RefVault.java make <vaultDir> <SIV_GCM|SIV_CTRMAC> <password>
//   java -cp ... RefVault.java dump <vaultDir> <password>          (one line per entry: type, path, size, sha256)
//   java -cp ... RefVault.java write <vaultDir> <password> <path> <text>
import org.cryptomator.cryptofs.CryptoFileSystemProperties;
import org.cryptomator.cryptofs.CryptoFileSystemProvider;
import org.cryptomator.cryptolib.api.CryptorProvider;
import org.cryptomator.cryptolib.api.Masterkey;
import org.cryptomator.cryptolib.api.MasterkeyLoader;
import org.cryptomator.cryptolib.common.MasterkeyFileAccess;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.stream.Stream;

public class RefVault {
    static final SecureRandom RNG = new SecureRandom();

    static CryptoFileSystemProperties props(Path vault, String password, CryptorProvider.Scheme scheme) {
        MasterkeyFileAccess mfa = new MasterkeyFileAccess(new byte[0], RNG);
        MasterkeyLoader loader = uri -> {
            try { return mfa.load(vault.resolve("masterkey.cryptomator"), password); }
            catch (Exception e) { throw new RuntimeException(e); }
        };
        var b = CryptoFileSystemProperties.cryptoFileSystemProperties().withKeyLoader(loader);
        if (scheme != null) b = b.withCipherCombo(scheme);
        return b.build();
    }

    public static void main(String[] args) throws Exception {
        Path vault = Paths.get(args[1]);
        switch (args[0]) {
            case "make" -> {
                Files.createDirectories(vault);
                String password = args[3];
                Masterkey mk = Masterkey.generate(RNG);
                new MasterkeyFileAccess(new byte[0], RNG).persist(mk, vault.resolve("masterkey.cryptomator"), password);
                var p = props(vault, password, CryptorProvider.Scheme.valueOf(args[2]));
                CryptoFileSystemProvider.initialize(vault, p, URI.create("masterkeyfile:masterkey.cryptomator"));
                try (FileSystem fs = CryptoFileSystemProvider.newFileSystem(vault, p)) {
                    Files.writeString(fs.getPath("/hello.txt"), "Hello from Cryptomator's own code.\n");
                    Files.write(fs.getPath("/empty.txt"), new byte[0]);
                    byte[] big = new byte[100_000];
                    for (int i = 0; i < big.length; i++) big[i] = (byte) (i * 31 + 7);
                    Files.write(fs.getPath("/big.bin"), big);
                    Files.createDirectories(fs.getPath("/Folder A/Sub folder"));
                    Files.writeString(fs.getPath("/Folder A/Sub folder/notes ü é 日本.txt"), "Unicode name and text: ü é 日本\n");
                    String longName = "a very long file name " + "x".repeat(140) + ".txt";
                    Files.writeString(fs.getPath("/Folder A/" + longName), "This name is long enough to be shortened.\n");
                    Files.createDirectories(fs.getPath("/" + "Long folder name " + "y".repeat(140)));
                    Files.writeString(fs.getPath("/" + "Long folder name " + "y".repeat(140) + "/inside.txt"), "Inside a long folder.\n");
                    Files.createSymbolicLink(fs.getPath("/link to hello"), fs.getPath("hello.txt"));
                }
                System.out.println("made " + vault);
            }
            case "dump" -> {
                var p = props(vault, args[2], null);
                try (FileSystem fs = CryptoFileSystemProvider.newFileSystem(vault, p);
                     Stream<Path> all = Files.walk(fs.getPath("/"))) {
                    all.sorted().forEach(path -> {
                        try {
                            if (path.toString().equals("/")) return;
                            if (Files.isSymbolicLink(path)) {
                                System.out.println("link\t" + path + "\t" + Files.readSymbolicLink(path));
                            } else if (Files.isDirectory(path)) {
                                System.out.println("dir\t" + path);
                            } else {
                                byte[] data = Files.readAllBytes(path);
                                String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
                                System.out.println("file\t" + path + "\t" + data.length + "\t" + sha);
                            }
                        } catch (Exception e) { throw new RuntimeException(e); }
                    });
                }
            }
            case "write" -> {
                var p = props(vault, args[2], null);
                try (FileSystem fs = CryptoFileSystemProvider.newFileSystem(vault, p)) {
                    Files.writeString(fs.getPath(args[3]), args[4], StandardCharsets.UTF_8);
                }
                System.out.println("wrote " + args[3]);
            }
            default -> throw new IllegalArgumentException("make | dump | write");
        }
    }
}
