module abs_diff_i276_o138(a,b,r);
input [137:0] a,b;
output [137:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
