module abs_diff_i84_o42(a,b,r);
input [41:0] a,b;
output [41:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
