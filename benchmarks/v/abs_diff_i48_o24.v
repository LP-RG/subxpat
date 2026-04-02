module abs_diff_i48_o24(a,b,r);
input [23:0] a,b;
output [23:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
