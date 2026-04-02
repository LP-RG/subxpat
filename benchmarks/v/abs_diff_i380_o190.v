module abs_diff_i380_o190(a,b,r);
input [189:0] a,b;
output [189:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
