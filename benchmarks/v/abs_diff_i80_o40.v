module abs_diff_i80_o40(a,b,r);
input [39:0] a,b;
output [39:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
