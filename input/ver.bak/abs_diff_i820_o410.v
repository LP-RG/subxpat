module abs_diff_i820_o410(a,b,r);
input [409:0] a,b;
output [409:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
