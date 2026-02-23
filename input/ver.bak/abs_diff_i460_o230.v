module abs_diff_i460_o230(a,b,r);
input [229:0] a,b;
output [229:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
