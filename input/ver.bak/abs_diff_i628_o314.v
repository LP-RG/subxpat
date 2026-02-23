module abs_diff_i628_o314(a,b,r);
input [313:0] a,b;
output [313:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
