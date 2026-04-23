module abs_diff_i65536_o32768(a,b,r);
input [32767:0] a,b;
output [32767:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
