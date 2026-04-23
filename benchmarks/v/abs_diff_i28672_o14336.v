module abs_diff_i28672_o14336(a,b,r);
input [14335:0] a,b;
output [14335:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
