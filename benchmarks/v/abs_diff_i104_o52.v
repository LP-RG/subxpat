module abs_diff_i104_o52(a,b,r);
input [51:0] a,b;
output [51:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
