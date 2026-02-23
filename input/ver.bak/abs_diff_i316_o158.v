module abs_diff_i316_o158(a,b,r);
input [157:0] a,b;
output [157:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
