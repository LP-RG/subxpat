module abs_diff_i596_o298(a,b,r);
input [297:0] a,b;
output [297:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
